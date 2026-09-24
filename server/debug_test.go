package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

const testDebugToken = "example-development-token-01234567890123456789"

func debugRequest(handler http.Handler, method, path, body, token string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, path, strings.NewReader(body))
	if token != "" {
		r.Header.Set("Authorization", "Bearer "+token)
	}
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, r)
	return w
}

func TestRemoteDebugOptInAndAuthentication(t *testing.T) {
	base := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusNoContent) })
	path := "/v1/loom-os/devices/dev-1/logs"
	if got := debugRequest(withDebugRoutes(base, nil), http.MethodGet, path, "", testDebugToken).Code; got != 404 {
		t.Fatalf("disabled endpoint returned %d", got)
	}
	if _, err := newDebugStore(t.TempDir(), "short"); err == nil {
		t.Fatal("weak token accepted")
	}
	store, err := newDebugStore(t.TempDir(), testDebugToken)
	if err != nil {
		t.Fatal(err)
	}
	handler := withDebugRoutes(base, store)
	for _, token := range []string{"", "wrong-development-token-012345678901234567890"} {
		if got := debugRequest(handler, http.MethodGet, path, "", token).Code; got != 401 {
			t.Fatalf("unauthorized request returned %d", got)
		}
	}
	if got := debugRequest(handler, http.MethodGet, "/v1/loom-os/devices/../logs", "", testDebugToken).Code; got != 404 {
		t.Fatalf("invalid device ID returned %d", got)
	}
	if got := debugRequest(handler, http.MethodGet, "/files/anything", "", "").Code; got != 204 {
		t.Fatalf("non-debug route changed: %d", got)
	}
}

func TestRemoteDebugUploadReadRetryAndRestart(t *testing.T) {
	root := t.TempDir()
	store, err := newDebugStore(root, testDebugToken)
	if err != nil {
		t.Fatal(err)
	}
	handler := withDebugRoutes(http.NotFoundHandler(), store)
	path := "/v1/loom-os/devices/dev-1/logs"
	batch := `{"session":"1","entries":[{"seq":1,"level":"INFO","source":"org.example.app","message":"started"}]}`
	for i := 0; i < 2; i++ {
		if got := debugRequest(handler, http.MethodPost, path, batch, testDebugToken).Code; got != 204 {
			t.Fatalf("POST returned %d", got)
		}
	}
	reboot := `{"session":"2","entries":[{"seq":1,"level":"ERROR","source":"runtime","message":"rebooted"}]}`
	if got := debugRequest(handler, http.MethodPost, path, reboot, testDebugToken).Code; got != 204 {
		t.Fatalf("POST after reboot returned %d", got)
	}
	// Data remains available after constructing a fresh store.
	store, err = newDebugStore(root, testDebugToken)
	if err != nil {
		t.Fatal(err)
	}
	handler = withDebugRoutes(http.NotFoundHandler(), store)
	response := debugRequest(handler, http.MethodGet, path, "", testDebugToken)
	if response.Code != 200 || response.Header().Get("Cache-Control") != "no-store" {
		t.Fatalf("GET returned %d", response.Code)
	}
	var result struct {
		DeviceID string       `json:"device_id"`
		Entries  []debugEntry `json:"entries"`
	}
	if err := json.Unmarshal(response.Body.Bytes(), &result); err != nil {
		t.Fatal(err)
	}
	if result.DeviceID != "dev-1" || len(result.Entries) != 2 ||
		result.Entries[1].Session != "2" || result.Entries[1].ReceivedAt == "" {
		t.Fatalf("incorrect log history: %+v", result)
	}
	response = debugRequest(handler, http.MethodGet, path+"?limit=1", "", testDebugToken)
	if err := json.Unmarshal(response.Body.Bytes(), &result); err != nil || len(result.Entries) != 1 || result.Entries[0].Message != "rebooted" {
		t.Fatalf("incorrect limited history: %+v, %v", result, err)
	}
}

func TestRemoteDebugRejectsOversizedAndInvalidBatches(t *testing.T) {
	store, err := newDebugStore(t.TempDir(), testDebugToken)
	if err != nil {
		t.Fatal(err)
	}
	handler := withDebugRoutes(http.NotFoundHandler(), store)
	path := "/v1/loom-os/devices/dev-1/logs"
	for _, tc := range []struct {
		body string
		want int
	}{
		{strings.Repeat("a", debugMaxBody+1), 413},
		{`{"session":"1","entries":[{"seq":1,"level":"INFO","source":"runtime","message":"ok"},{"seq":2,"level":"WARN","source":"runtime","message":"ok"}]}`, 204},
		{`{"session":"1","entries":[{"seq":3,"level":"INFO","source":"../escape","message":"bad"}]}`, 400},
		{`{"session":"1","entries":[{"seq":3,"level":"DEBUG","source":"runtime","message":"bad"}]}`, 400},
		{`{"session":"evil","entries":[{"seq":3,"level":"INFO","source":"runtime","message":"bad"}]}`, 400},
	} {
		if got := debugRequest(handler, http.MethodPost, path, tc.body, testDebugToken).Code; got != tc.want {
			t.Fatalf("POST returned %d, want %d", got, tc.want)
		}
	}
	if got := debugRequest(handler, http.MethodGet, path+"?limit=201", "", testDebugToken).Code; got != 400 {
		t.Fatalf("invalid limit returned %d", got)
	}
}
