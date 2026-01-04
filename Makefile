LOCAL_BIN=./bin

$(LOCAL_BIN):
	mkdir -p $(LOCAL_BIN)

MDBOOK_VERSION ?= v0.5.2
MDBOOK_URL=https://github.com/rust-lang/mdBook/releases/download/$(MDBOOK_VERSION)/mdbook-$(MDBOOK_VERSION)-x86_64-unknown-linux-gnu.tar.gz

mdbook: $(LOCAL_BIN)
	test -f $(LOCAL_BIN)/mdbook || wget $(MDBOOK_URL) -O - | tar xz -C $(LOCAL_BIN) mdbook

gen-summary:
	cd src && \
	python3 ../tools/gen-summary.py  > ./SUMMARY.md

build: mdbook gen-summary
	$(LOCAL_BIN)/mdbook build -d ./book
