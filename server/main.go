package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"mime"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

func jsonError(w http.ResponseWriter, status int, message string) {
	body, _ := json.Marshal(map[string]string{"error": message})
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write(body)
}

func oneQueryValue(values map[string][]string, key string) (string, bool) {
	items := values[key]
	returnValue := ""
	if len(items) == 1 {
		returnValue = items[0]
	}
	return returnValue, len(items) == 1 && returnValue != ""
}

func releaseHandler(store ReleaseStore) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			jsonError(w, http.StatusMethodNotAllowed, "method not allowed")
			return
		}
		switch {
		case r.URL.Path == "/v1/loom-os/releases/latest":
			serveLatest(w, r, store)
		case strings.HasPrefix(r.URL.Path, "/files/"):
			serveFile(w, r, store)
		default:
			jsonError(w, http.StatusNotFound, "not found")
		}
	})
}

func serveLatest(w http.ResponseWriter, r *http.Request, store ReleaseStore) {
	params := r.URL.Query()
	board, okBoard := oneQueryValue(params, "board")
	channel, okChannel := oneQueryValue(params, "channel")
	current, okCurrent := oneQueryValue(params, "current")
	bootstrap, okBootstrap := oneQueryValue(params, "bootstrap")
	if !okBoard || !okChannel || !okCurrent || !okBootstrap {
		jsonError(w, http.StatusBadRequest, "board, channel, current and bootstrap are required")
		return
	}
	if err := validateBoard(board); err != nil {
		jsonError(w, http.StatusBadRequest, err.Error())
		return
	}
	if _, ok := channelRank[channel]; !ok {
		jsonError(w, http.StatusBadRequest, "invalid channel")
		return
	}
	if _, err := parseVersion(current); err != nil {
		jsonError(w, http.StatusBadRequest, err.Error())
		return
	}
	if _, err := parseVersion(bootstrap); err != nil {
		jsonError(w, http.StatusBadRequest, err.Error())
		return
	}
	boardRoot, _ := store.boardRoot(board)
	info, err := os.Stat(boardRoot)
	if errors.Is(err, os.ErrNotExist) || err == nil && !info.IsDir() {
		jsonError(w, http.StatusNotFound, "unsupported board")
		return
	}
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "release store unavailable")
		return
	}
	m, err := store.latest(board, channel, current, bootstrap)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "release store unavailable")
		return
	}
	if m == nil {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	body, err := json.Marshal(m)
	if err != nil {
		jsonError(w, http.StatusInternalServerError, "invalid release manifest")
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
}

func serveFile(w http.ResponseWriter, r *http.Request, store ReleaseStore) {
	parts := strings.SplitN(strings.TrimPrefix(r.URL.Path, "/files/"), "/", 3)
	if len(parts) != 3 || parts[0] == "" || parts[1] == "" || parts[2] == "" {
		jsonError(w, http.StatusNotFound, "not found")
		return
	}
	file, err := store.resolveFile(parts[0], parts[1], parts[2])
	if err != nil {
		jsonError(w, http.StatusNotFound, "not found")
		return
	}
	data, err := os.ReadFile(file)
	if err != nil {
		jsonError(w, http.StatusNotFound, "not found")
		return
	}
	contentType := mime.TypeByExtension(filepath.Ext(file))
	if contentType == "" {
		contentType = "application/octet-stream"
	}
	w.Header().Set("Content-Type", contentType)
	w.Header().Set("Content-Length", strconv.Itoa(len(data)))
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(data)
}

func serve(args []string) error {
	flags := flag.NewFlagSet("serve", flag.ContinueOnError)
	root := os.Getenv("LOOM_OS_RELEASE_ROOT")
	if root == "" {
		root = "./release-data"
	}
	rootFlag := flags.String("root", root, "release store directory")
	host := flags.String("host", "127.0.0.1", "listen address")
	port := flags.Int("port", 8080, "listen port")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if len(flags.Args()) != 0 || *port < 1 || *port > 65535 {
		return errors.New("invalid serve arguments")
	}
	store, err := newReleaseStore(*rootFlag)
	if err != nil {
		return err
	}
	address := net.JoinHostPort(*host, strconv.Itoa(*port))
	fmt.Printf("Loom OS release server: http://%s root=%s\n", address, store.Root)
	fmt.Println("Production deployment must put this service behind HTTPS termination.")
	server := &http.Server{Addr: address, Handler: releaseHandler(store), ReadHeaderTimeout: 10 * time.Second}
	return server.ListenAndServe()
}

func run(args []string) error {
	if len(args) < 1 {
		return errors.New("usage: release-server <serve|publish> [options]")
	}
	switch args[0] {
	case "serve":
		return serve(args[1:])
	case "publish":
		return publish(args[1:])
	default:
		return fmt.Errorf("unknown command %q; use serve or publish", args[0])
	}
}

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
