package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"strings"
)

func releaseFileURL(base, board, version, relative string) string {
	segments := strings.Split(relative, "/")
	for i := range segments {
		segments[i] = url.PathEscape(segments[i])
	}
	return strings.TrimRight(base, "/") + "/files/" +
		url.PathEscape(board) + "/" + url.PathEscape(version) + "/" + strings.Join(segments, "/")
}

func withinRoot(root, candidate string) bool {
	relative, err := filepath.Rel(root, candidate)
	return err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator))
}

func copyFile(source, destination string) (int64, error) {
	input, err := os.Open(source)
	if err != nil {
		return 0, err
	}
	defer input.Close()
	output, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if err != nil {
		return 0, err
	}
	written, copyErr := io.Copy(output, input)
	closeErr := output.Close()
	if copyErr != nil {
		return 0, copyErr
	}
	if closeErr != nil {
		return 0, closeErr
	}
	return written, nil
}

func publishRelease(store ReleaseStore, sourceRoot, manifestPath, baseURL string) (string, error) {
	base, err := url.Parse(baseURL)
	if err != nil || base.Scheme != "https" || base.Host == "" || base.RawQuery != "" || base.Fragment != "" {
		return "", errors.New("public base URL must use HTTPS without query or fragment")
	}
	sourceRoot, err = filepath.Abs(sourceRoot)
	if err != nil {
		return "", err
	}
	sourceRoot, err = filepath.EvalSymlinks(sourceRoot)
	if err != nil {
		return "", err
	}
	sourceInfo, err := os.Stat(sourceRoot)
	if err != nil || !sourceInfo.IsDir() {
		return "", errors.New("source root must be a directory")
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return "", err
	}
	var manifest Manifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return "", err
	}
	if _, err := parseVersion(manifest.Version); err != nil {
		return "", err
	}
	target, err := store.releaseRoot(manifest.Board, manifest.Version)
	if err != nil {
		return "", err
	}
	if _, err := os.Lstat(target); err == nil {
		return "", fmt.Errorf("release already exists and is immutable: %s", target)
	} else if !errors.Is(err, os.ErrNotExist) {
		return "", err
	}
	if len(manifest.Files) == 0 {
		return "", errors.New("manifest files are required")
	}

	sources := make([]string, len(manifest.Files))
	for i := range manifest.Files {
		file := &manifest.Files[i]
		if !safeRelative(file.Path) {
			return "", fmt.Errorf("invalid file path: %q", file.Path)
		}
		source, err := filepath.EvalSymlinks(filepath.Join(sourceRoot, filepath.FromSlash(file.Path)))
		if err != nil {
			return "", fmt.Errorf("source file missing: %s: %w", file.Path, err)
		}
		if !withinRoot(sourceRoot, source) {
			return "", fmt.Errorf("source path escaped source root: %s", file.Path)
		}
		info, err := os.Stat(source)
		if err != nil || !info.Mode().IsRegular() {
			return "", fmt.Errorf("source file missing: %s", file.Path)
		}
		file.Size = info.Size()
		file.URL = releaseFileURL(baseURL, manifest.Board, manifest.Version, file.Path)
		sources[i] = source
	}
	if _, err := validateManifest(manifest); err != nil {
		return "", err
	}

	parent := filepath.Dir(target)
	if err := os.MkdirAll(parent, 0755); err != nil {
		return "", err
	}
	tmp, err := os.MkdirTemp(parent, "."+manifest.Version+".publishing-")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(tmp)
	for i, file := range manifest.Files {
		destination := filepath.Join(tmp, filepath.FromSlash(file.Path))
		if err := os.MkdirAll(filepath.Dir(destination), 0755); err != nil {
			return "", err
		}
		written, err := copyFile(sources[i], destination)
		if err != nil {
			return "", err
		}
		if written != file.Size {
			return "", fmt.Errorf("copied size mismatch: %s", file.Path)
		}
	}
	body, err := json.MarshalIndent(manifest, "", "  ")
	if err != nil {
		return "", err
	}
	body = append(body, '\n')
	if err := os.WriteFile(filepath.Join(tmp, "manifest.json"), body, 0644); err != nil {
		return "", err
	}
	if _, err := os.Lstat(target); err == nil {
		return "", fmt.Errorf("release already exists and is immutable: %s", target)
	} else if !errors.Is(err, os.ErrNotExist) {
		return "", err
	}
	if err := os.Rename(tmp, target); err != nil {
		return "", err
	}
	return target, nil
}

func publish(args []string) error {
	flags := flag.NewFlagSet("publish", flag.ContinueOnError)
	storeRoot := flags.String("store-root", "", "release store directory")
	sourceRoot := flags.String("source-root", "", "source Runtime directory")
	manifestPath := flags.String("manifest", "", "manifest template with canonical file paths")
	publicBaseURL := flags.String("public-base-url", "", "public HTTPS base URL")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if len(flags.Args()) != 0 || *storeRoot == "" || *sourceRoot == "" || *manifestPath == "" || *publicBaseURL == "" {
		return errors.New("publish requires -store-root, -source-root, -manifest and -public-base-url")
	}
	store, err := newReleaseStore(*storeRoot)
	if err != nil {
		return err
	}
	target, err := publishRelease(store, *sourceRoot, *manifestPath, *publicBaseURL)
	if err != nil {
		return err
	}
	fmt.Printf("published %s -> %s\n", filepath.Base(target), target)
	return nil
}
