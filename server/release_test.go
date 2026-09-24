package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func fixtureManifest(version, channel, minBootstrap string) Manifest {
	return Manifest{
		Schema: 1, Product: "clawos", Board: "esp-mosaico", Channel: channel,
		Version: version, ReleaseID: "clawos:esp-mosaico:" + version,
		Entry: "main.lua", MinBootstrap: minBootstrap,
		Files: []ReleaseFile{{
			Path: "main.lua",
			URL: "https://updates.example.com/files/esp-mosaico/" + version + "/main.lua",
			Size: 10,
		}},
	}
}

func writeRelease(t *testing.T, store ReleaseStore, version, channel, bootstrap string) Manifest {
	t.Helper()
	m := fixtureManifest(version, channel, bootstrap)
	root, err := store.releaseRoot("esp-mosaico", version)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	data := []byte("return {}\n")
	if err := os.WriteFile(filepath.Join(root, "main.lua"), data, 0644); err != nil {
		t.Fatal(err)
	}
	m.Files[0].Size = int64(len(data))
	body, err := json.Marshal(m)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, "manifest.json"), body, 0644); err != nil {
		t.Fatal(err)
	}
	return m
}

func TestVersionOrderingAndValidation(t *testing.T) {
	ordered := []string{
		"0.1.9", "0.1.10", "0.2.0-dev.9", "0.2.0-beta.1",
		"0.2.0-beta.9", "0.2.0-rc.1", "0.2.0",
	}
	for i := 1; i < len(ordered); i++ {
		previous, err := parseVersion(ordered[i-1])
		if err != nil {
			t.Fatal(err)
		}
		next, err := parseVersion(ordered[i])
		if err != nil || previous.Compare(next) >= 0 {
			t.Fatalf("expected %s < %s: %v", previous.Raw, next.Raw, err)
		}
	}
	for _, invalid := range []string{"v0.1.0", "0.01.0", "latest", "0.1.0+build.1", "0.2.0-dev.0"} {
		if _, err := parseVersion(invalid); err == nil {
			t.Errorf("accepted invalid version %q", invalid)
		}
	}
	large, err := parseVersion("999999999999999999.0.0")
	if err != nil || large.Compare(Version{major: "1", minor: "0", patch: "0", rank: 4, sequence: "0"}) <= 0 {
		t.Fatal("large numeric version comparison failed", err)
	}
}

func TestManifestValidation(t *testing.T) {
	valid := fixtureManifest("0.1.1", "stable", "0.1.0")
	if _, err := validateManifest(valid); err != nil {
		t.Fatal(err)
	}
	badChannel := fixtureManifest("0.2.0-beta.1", "stable", "0.1.0")
	if _, err := validateManifest(badChannel); err == nil {
		t.Fatal("accepted channel mismatch")
	}
	for _, badPath := range []string{"../main.lua", "/main.lua", "core//main.lua", "core/./main.lua", "core\\main.lua"} {
		bad := valid
		bad.Files = []ReleaseFile{{Path: badPath, URL: valid.Files[0].URL, Size: 10}}
		if _, err := validateManifest(bad); err == nil {
			t.Errorf("accepted invalid path %q", badPath)
		}
	}
	badURL := valid
	badURL.Files = []ReleaseFile{{Path: "main.lua", URL: "http://example.com/main.lua", Size: 10}}
	if _, err := validateManifest(badURL); err == nil {
		t.Fatal("accepted HTTP file URL")
	}
	badSize := valid
	badSize.Files = []ReleaseFile{{Path: "main.lua", URL: valid.Files[0].URL, Size: 0}}
	if _, err := validateManifest(badSize); err == nil {
		t.Fatal("accepted zero size")
	}
	duplicate := valid
	duplicate.Files = append(append([]ReleaseFile{}, valid.Files...), valid.Files[0])
	if _, err := validateManifest(duplicate); err == nil {
		t.Fatal("accepted duplicate path")
	}
}

func TestLatestAndBootstrapFilter(t *testing.T) {
	store, err := newReleaseStore(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	writeRelease(t, store, "0.1.1", "stable", "0.1.0")
	writeRelease(t, store, "0.1.10", "stable", "0.1.0")
	writeRelease(t, store, "0.2.0-beta.1", "beta", "0.1.0")
	selected, err := store.latest("esp-mosaico", "stable", "0.1.0", "0.1.0")
	if err != nil || selected == nil || selected.Version != "0.1.10" {
		t.Fatalf("wrong latest release: %+v, %v", selected, err)
	}
	if selected, err := store.latest("esp-mosaico", "stable", "0.1.10", "0.1.0"); err != nil || selected != nil {
		t.Fatalf("equal version returned: %+v, %v", selected, err)
	}
	writeRelease(t, store, "0.1.11", "stable", "0.2.0")
	if selected, err := store.latest("esp-mosaico", "stable", "0.1.10", "0.1.0"); err != nil || selected != nil {
		t.Fatalf("bootstrap-incompatible release returned: %+v, %v", selected, err)
	}
}

func TestHTTPContractAndFileWhitelist(t *testing.T) {
	store, err := newReleaseStore(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	writeRelease(t, store, "0.1.1", "stable", "0.1.0")
	handler := releaseHandler(store)
	cases := []struct {
		path string
		status int
		want string
	}{
		{"/v1/clawos/releases/latest?board=esp-mosaico&channel=stable&current=0.1.0&bootstrap=0.1.0", 200, "\"version\":\"0.1.1\""},
		{"/v1/clawos/releases/latest?board=esp-mosaico&channel=stable&current=0.1.1&bootstrap=0.1.0", 204, ""},
		{"/v1/clawos/releases/latest?board=esp-mosaico&channel=stable&current=bad&bootstrap=0.1.0", 400, "invalid ClawOS version"},
		{"/v1/clawos/releases/latest?board=esp-mosaico&board=other&channel=stable&current=0.1.0&bootstrap=0.1.0", 400, "required"},
		{"/v1/clawos/releases/latest?board=other&channel=stable&current=0.1.0&bootstrap=0.1.0", 404, "unsupported board"},
		{"/files/esp-mosaico/0.1.1/main.lua", 200, "return {}\n"},
		{"/files/esp-mosaico/0.1.1/secret.lua", 404, "not found"},
		{"/files/esp-mosaico/0.1.1/%2e%2e/main.lua", 404, "not found"},
	}
	for _, tc := range cases {
		t.Run(tc.path, func(t *testing.T) {
			recorder := httptest.NewRecorder()
			handler.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, tc.path, nil))
			if recorder.Code != tc.status || !strings.Contains(recorder.Body.String(), tc.want) {
				t.Fatalf("got %d %q; want %d containing %q", recorder.Code, recorder.Body.String(), tc.status, tc.want)
			}
			if tc.status == 204 && recorder.Body.Len() != 0 {
				t.Fatal("204 response included a body")
			}
		})
	}
}

func TestPublishImmutableAndEscapesURL(t *testing.T) {
	base := t.TempDir()
	source := filepath.Join(base, "source")
	if err := os.MkdirAll(filepath.Join(source, "lib"), 0755); err != nil {
		t.Fatal(err)
	}
	mainData := []byte("return {}\n")
	assetData := []byte("return 'ok'\n")
	if err := os.WriteFile(filepath.Join(source, "main.lua"), mainData, 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "lib", "a b.lua"), assetData, 0644); err != nil {
		t.Fatal(err)
	}
	m := fixtureManifest("0.1.1", "stable", "0.1.0")
	m.Files = append(m.Files, ReleaseFile{Path: "lib/a b.lua"})
	template, err := json.Marshal(m)
	if err != nil {
		t.Fatal(err)
	}
	templatePath := filepath.Join(base, "template.json")
	if err := os.WriteFile(templatePath, template, 0644); err != nil {
		t.Fatal(err)
	}
	store, err := newReleaseStore(filepath.Join(base, "releases"))
	if err != nil {
		t.Fatal(err)
	}
	target, err := publishRelease(store, source, templatePath, "https://updates.example.com/base/")
	if err != nil {
		t.Fatal(err)
	}
	published, err := store.loadManifest("esp-mosaico", "0.1.1")
	if err != nil {
		t.Fatal(err)
	}
	if published.Files[0].Size != int64(len(mainData)) ||
		published.Files[1].Size != int64(len(assetData)) ||
		published.Files[1].URL != "https://updates.example.com/base/files/esp-mosaico/0.1.1/lib/a%20b.lua" {
		t.Fatalf("incorrect published manifest: %+v", published.Files)
	}
	if data, err := os.ReadFile(filepath.Join(target, "lib", "a b.lua")); err != nil || string(data) != string(assetData) {
		t.Fatalf("incorrect published file: %q, %v", data, err)
	}
	if _, err := publishRelease(store, source, templatePath, "https://updates.example.com"); err == nil {
		t.Fatal("allowed overwrite of immutable release")
	}
}

func TestPublishRejectsEscapingSource(t *testing.T) {
	base := t.TempDir()
	source := filepath.Join(base, "source")
	if err := os.Mkdir(source, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(base, "outside.lua"), []byte("return 1\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(filepath.Join(base, "outside.lua"), filepath.Join(source, "main.lua")); err != nil {
		t.Skipf("symlinks unavailable: %v", err)
	}
	m := fixtureManifest("0.1.1", "stable", "0.1.0")
	body, _ := json.Marshal(m)
	manifestPath := filepath.Join(base, "template.json")
	if err := os.WriteFile(manifestPath, body, 0644); err != nil {
		t.Fatal(err)
	}
	store, err := newReleaseStore(filepath.Join(base, "releases"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := publishRelease(store, source, manifestPath, "https://updates.example.com"); err == nil {
		t.Fatal("published a source symlink escaping the source root")
	}
}
