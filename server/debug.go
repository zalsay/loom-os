package main

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

const debugMaxBody = 32 << 10
const debugMaxEntries = 200

var debugID = regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)
var debugSource = regexp.MustCompile(`^[A-Za-z0-9._-]{1,64}$`)

type debugEntry struct {
	Session    string `json:"session"`
	Seq        uint64 `json:"seq"`
	Level      string `json:"level"`
	Source     string `json:"source"`
	Message    string `json:"message"`
	ReceivedAt string `json:"received_at,omitempty"`
}

type debugStore struct {
	root  string
	token [32]byte
	mu    sync.Mutex
}

func newDebugStore(root, token string) (*debugStore, error) {
	if len(token) < 32 || len(token) > 256 || strings.ContainsAny(token, "\r\n") {
		return nil, errors.New("LOOM_OS_DEBUG_TOKEN must contain 32–256 characters without newlines")
	}
	if err := os.MkdirAll(root, 0700); err != nil {
		return nil, err
	}
	return &debugStore{root: root, token: sha256.Sum256([]byte(token))}, nil
}

func (s *debugStore) authorized(r *http.Request) bool {
	value := r.Header.Get("Authorization")
	if !strings.HasPrefix(value, "Bearer ") {
		return false
	}
	provided := sha256.Sum256([]byte(strings.TrimPrefix(value, "Bearer ")))
	return subtle.ConstantTimeCompare(provided[:], s.token[:]) == 1
}

func (s *debugStore) file(device string) string {
	return filepath.Join(s.root, device+".json")
}

func (s *debugStore) read(device string) ([]debugEntry, error) {
	data, err := os.ReadFile(s.file(device))
	if errors.Is(err, os.ErrNotExist) {
		return []debugEntry{}, nil
	}
	if err != nil {
		return nil, err
	}
	var entries []debugEntry
	if err := json.Unmarshal(data, &entries); err != nil {
		return nil, err
	}
	return entries, nil
}

func (s *debugStore) handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	if !s.authorized(r) {
		jsonError(w, http.StatusUnauthorized, "unauthorized")
		return
	}
	path := strings.TrimPrefix(r.URL.Path, "/v1/loom-os/devices/")
	if !strings.HasSuffix(path, "/logs") || !debugID.MatchString(strings.TrimSuffix(path, "/logs")) {
		jsonError(w, http.StatusNotFound, "not found")
		return
	}
	device := strings.TrimSuffix(path, "/logs")
	switch r.Method {
	case http.MethodGet:
		limit := 100
		if raw := r.URL.Query().Get("limit"); raw != "" {
			var err error
			limit, err = strconv.Atoi(raw)
			if err != nil || limit < 1 || limit > debugMaxEntries {
				jsonError(w, http.StatusBadRequest, "limit must be 1–200")
				return
			}
		}
		s.mu.Lock()
		entries, err := s.read(device)
		s.mu.Unlock()
		if err != nil {
			jsonError(w, http.StatusInternalServerError, "log store unavailable")
			return
		}
		if len(entries) > limit {
			entries = entries[len(entries)-limit:]
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(struct {
			DeviceID string       `json:"device_id"`
			Entries  []debugEntry `json:"entries"`
		}{device, entries})
	case http.MethodPost:
		if r.ContentLength > debugMaxBody {
			jsonError(w, http.StatusRequestEntityTooLarge, "log batch exceeds 32 KiB")
			return
		}
		data, err := io.ReadAll(io.LimitReader(r.Body, debugMaxBody+1))
		if err != nil || len(data) > debugMaxBody {
			jsonError(w, http.StatusRequestEntityTooLarge, "log batch exceeds 32 KiB")
			return
		}
		var batch struct {
			Session string       `json:"session"`
			Entries []debugEntry `json:"entries"`
		}
		if err := json.Unmarshal(data, &batch); err != nil || len(batch.Entries) < 1 || len(batch.Entries) > 16 ||
			len(batch.Session) < 1 || len(batch.Session) > 32 || strings.Trim(batch.Session, "0123456789") != "" {
			jsonError(w, http.StatusBadRequest, "invalid log batch")
			return
		}
		for i := range batch.Entries {
			e := &batch.Entries[i]
			if e.Seq == 0 || !debugSource.MatchString(e.Source) ||
				len(e.Message) > 512 ||
				(e.Level != "INFO" && e.Level != "WARN" && e.Level != "ERROR") {
				jsonError(w, http.StatusBadRequest, "invalid log entry")
				return
			}
			e.Session = batch.Session
			e.ReceivedAt = time.Now().UTC().Format(time.RFC3339Nano)
		}
		s.mu.Lock()
		entries, err := s.read(device)
		if err == nil {
			// Sequence numbers restart on each device boot; retrying a batch is idempotent.
			seen := make(map[string]bool, len(entries))
			for _, entry := range entries {
				seen[entry.Session+":"+strconv.FormatUint(entry.Seq, 10)] = true
			}
			for _, entry := range batch.Entries {
				key := entry.Session + ":" + strconv.FormatUint(entry.Seq, 10)
				if !seen[key] {
					entries = append(entries, entry)
					seen[key] = true
				}
			}
			if len(entries) > debugMaxEntries {
				entries = entries[len(entries)-debugMaxEntries:]
			}
			var body []byte
			body, err = json.Marshal(entries)
			if err == nil {
				var tmp *os.File
				tmp, err = os.CreateTemp(s.root, ".logs-*")
				if err == nil {
					defer os.Remove(tmp.Name())
					if _, err = tmp.Write(body); err == nil {
						err = tmp.Chmod(0600)
					}
					if closeErr := tmp.Close(); err == nil {
						err = closeErr
					}
					if err == nil {
						err = os.Rename(tmp.Name(), s.file(device))
					}
				}
			}
		}
		s.mu.Unlock()
		if err != nil {
			jsonError(w, http.StatusInternalServerError, "log store unavailable")
			return
		}
		w.WriteHeader(http.StatusNoContent)
	default:
		w.Header().Set("Allow", "GET, POST")
		jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
	}
}

func withDebugRoutes(next http.Handler, s *debugStore) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/v1/loom-os/devices/") {
			if s == nil {
				jsonError(w, http.StatusNotFound, "not found")
			} else {
				s.handler(w, r)
			}
			return
		}
		next.ServeHTTP(w, r)
	})
}
