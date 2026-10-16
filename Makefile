CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -Os
CPPFLAGS += -Iinclude
BUILD ?= build
SANITIZE ?=
.PHONY: all test sanitize generated clean
all: $(BUILD)/fixture $(BUILD)/test_mib
$(BUILD):
	mkdir -p $(BUILD)
$(BUILD)/fixture: tests/fixture.c src/sg_stats.c include/sg_stats.h include/sg_fields.h src/sg_fields.inc | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SANITIZE) -fstack-usage src/sg_stats.c tests/fixture.c -o $@
$(BUILD)/test_mib: tests/test_mib.c src/sg_mib.c include/sg_mib.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SANITIZE) -fstack-usage src/sg_mib.c tests/test_mib.c -o $@
test: all
	python3 tests/test_serializer.py $(BUILD)/fixture
	$(BUILD)/test_mib
sanitize:
	$(MAKE) BUILD=build-sanitize CFLAGS='-std=c99 -Wall -Wextra -Werror -O1 -g' SANITIZE='-fsanitize=address,undefined -fno-omit-frame-pointer -fno-pie -no-pie' test
generated:
	python3 tools/generate_fields.py
clean:
	$(RM) -r build build-sanitize
