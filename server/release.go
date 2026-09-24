package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var (
	versionRE = regexp.MustCompile(`^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(dev|beta|rc)\.([1-9][0-9]*))?$`)
	boardRE   = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)
	channelRank = map[string]int{"dev": 1, "beta": 2, "rc": 3, "stable": 4}
)

type Version struct {
	Raw, Channel       string
	major, minor, patch string
	sequence            string
	rank                int
}

func parseVersion(raw string) (Version, error) {
	if raw == "" || len(raw) > 32 {
		return Version{}, errors.New("version must be a non-empty string up to 32 characters")
	}
	m := versionRE.FindStringSubmatch(raw)
	if m == nil {
		return Version{}, errors.New("invalid Loom OS version")
	}
	channel, sequence := m[4], m[5]
	if channel == "" {
		channel, sequence = "stable", "0"
	}
	return Version{
		Raw: raw, Channel: channel,
		major: m[1], minor: m[2], patch: m[3],
		sequence: sequence, rank: channelRank[channel],
	}, nil
}

func compareDigits(a, b string) int {
	if len(a) < len(b) {
		return -1
	}
	if len(a) > len(b) {
		return 1
	}
	return strings.Compare(a, b)
}

func (v Version) Compare(other Version) int {
	for _, pair := range [][2]string{{v.major, other.major}, {v.minor, other.minor}, {v.patch, other.patch}} {
		if n := compareDigits(pair[0], pair[1]); n != 0 {
			return n
		}
	}
	if v.rank < other.rank {
		return -1
	}
	if v.rank > other.rank {
		return 1
	}
	return compareDigits(v.sequence, other.sequence)
}

func validateBoard(board string) error {
	if !boardRE.MatchString(board) {
		return errors.New("invalid board")
	}
	return nil
}

func safeRelative(relative string) bool {
	if relative == "" || strings.HasPrefix(relative, "/") || strings.Contains(relative, "\\") {
		return false
	}
	for _, segment := range strings.Split(relative, "/") {
		if segment == "" || segment == "." || segment == ".." {
			return false
		}
	}
	return true
}

type ReleaseFile struct {
	Path string `json:"path"`
	URL  string `json:"url"`
	Size int64  `json:"size"`
}

type Manifest struct {
	Schema       int           `json:"schema"`
	Product      string        `json:"product"`
	Board        string        `json:"board"`
	Channel      string        `json:"channel"`
	Version      string        `json:"version"`
	ReleaseID    string        `json:"release_id"`
	Entry        string        `json:"entry"`
	MinBootstrap string        `json:"min_bootstrap"`
	Files        []ReleaseFile `json:"files"`
}

func validateManifest(m Manifest) (Version, error) {
	if m.Schema != 1 {
		return Version{}, errors.New("schema must be 1")
	}
	if m.Product != "loom-os" {
		return Version{}, errors.New("product must be loom-os")
	}
	if err := validateBoard(m.Board); err != nil {
		return Version{}, err
	}
	if _, ok := channelRank[m.Channel]; !ok {
		return Version{}, errors.New("invalid channel")
	}
	version, err := parseVersion(m.Version)
	if err != nil {
		return Version{}, err
	}
	if version.Channel != m.Channel {
		return Version{}, errors.New("version suffix does not match channel")
	}
	if expected := fmt.Sprintf("loom-os:%s:%s", m.Board, m.Version); m.ReleaseID != expected {
		return Version{}, fmt.Errorf("release_id must equal %s", expected)
	}
	if m.Entry != "main.lua" {
		return Version{}, errors.New("entry must be main.lua")
	}
	if _, err := parseVersion(m.MinBootstrap); err != nil {
		return Version{}, err
	}
	if len(m.Files) == 0 {
		return Version{}, errors.New("files must be a non-empty array")
	}
	seen := make(map[string]bool, len(m.Files))
	for _, file := range m.Files {
		if !safeRelative(file.Path) {
			return Version{}, fmt.Errorf("invalid file path: %q", file.Path)
		}
		if seen[file.Path] {
			return Version{}, fmt.Errorf("duplicate file path: %s", file.Path)
		}
		seen[file.Path] = true
		u, err := url.Parse(file.URL)
		if err != nil || u.Scheme != "https" || u.Host == "" {
			return Version{}, fmt.Errorf("file url must use HTTPS: %s", file.Path)
		}
		if file.Size < 1 {
			return Version{}, fmt.Errorf("file size must be a positive integer: %s", file.Path)
		}
	}
	if !seen["main.lua"] {
		return Version{}, errors.New("files must include main.lua")
	}
	return version, nil
}

type ReleaseStore struct{ Root string }

func newReleaseStore(root string) (ReleaseStore, error) {
	absolute, err := filepath.Abs(root)
	if err != nil {
		return ReleaseStore{}, err
	}
	if resolved, err := filepath.EvalSymlinks(absolute); err == nil {
		absolute = resolved
	} else if !errors.Is(err, os.ErrNotExist) {
		return ReleaseStore{}, err
	}
	return ReleaseStore{Root: absolute}, nil
}

func (s ReleaseStore) boardRoot(board string) (string, error) {
	if err := validateBoard(board); err != nil {
		return "", err
	}
	return filepath.Join(s.Root, "loom-os", board), nil
}

func (s ReleaseStore) releaseRoot(board, version string) (string, error) {
	if _, err := parseVersion(version); err != nil {
		return "", err
	}
	root, err := s.boardRoot(board)
	if err != nil {
		return "", err
	}
	return filepath.Join(root, version), nil
}

func (s ReleaseStore) loadManifest(board, version string) (Manifest, error) {
	root, err := s.releaseRoot(board, version)
	if err != nil {
		return Manifest{}, err
	}
	data, err := os.ReadFile(filepath.Join(root, "manifest.json"))
	if err != nil {
		return Manifest{}, err
	}
	var m Manifest
	if err := json.Unmarshal(data, &m); err != nil {
		return Manifest{}, err
	}
	if _, err := validateManifest(m); err != nil {
		return Manifest{}, err
	}
	if m.Board != board || m.Version != version {
		return Manifest{}, errors.New("manifest identity does not match directory")
	}
	return m, nil
}

func (s ReleaseStore) latest(board, channel, current, bootstrap string) (*Manifest, error) {
	root, err := s.boardRoot(board)
	if err != nil {
		return nil, err
	}
	if _, ok := channelRank[channel]; !ok {
		return nil, errors.New("invalid channel")
	}
	currentVersion, err := parseVersion(current)
	if err != nil {
		return nil, err
	}
	bootstrapVersion, err := parseVersion(bootstrap)
	if err != nil {
		return nil, err
	}
	entries, err := os.ReadDir(root)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var selected *Manifest
	var selectedVersion Version
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		if _, err := parseVersion(entry.Name()); err != nil {
			continue
		}
		m, err := s.loadManifest(board, entry.Name())
		if err != nil || m.Channel != channel {
			continue
		}
		version, _ := parseVersion(m.Version)
		minBootstrap, _ := parseVersion(m.MinBootstrap)
		if version.Compare(currentVersion) <= 0 || minBootstrap.Compare(bootstrapVersion) > 0 {
			continue
		}
		if selected == nil || version.Compare(selectedVersion) > 0 {
			copy := m
			selected, selectedVersion = &copy, version
		}
	}
	return selected, nil
}

func (s ReleaseStore) resolveFile(board, version, relative string) (string, error) {
	if !safeRelative(relative) {
		return "", errors.New("invalid file path")
	}
	root, err := s.releaseRoot(board, version)
	if err != nil {
		return "", err
	}
	m, err := s.loadManifest(board, version)
	if err != nil {
		return "", err
	}
	allowed := false
	for _, file := range m.Files {
		if file.Path == relative {
			allowed = true
			break
		}
	}
	if !allowed {
		return "", errors.New("file is not part of published manifest")
	}
	resolvedRoot, err := filepath.EvalSymlinks(root)
	if err != nil {
		return "", err
	}
	candidate, err := filepath.EvalSymlinks(filepath.Join(root, filepath.FromSlash(relative)))
	if err != nil {
		return "", err
	}
	within, err := filepath.Rel(resolvedRoot, candidate)
	if err != nil || within == ".." || strings.HasPrefix(within, ".."+string(filepath.Separator)) {
		return "", errors.New("file path escaped release root")
	}
	info, err := os.Stat(candidate)
	if err != nil {
		return "", err
	}
	if !info.Mode().IsRegular() {
		return "", errors.New("not a regular file")
	}
	return candidate, nil
}
