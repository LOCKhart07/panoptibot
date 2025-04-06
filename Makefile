.PHONY: format
format:
	uvx ruff check --select I --fix
	uvx ruff format


.PHONY: run
run:
	uv run python run.py


.PHONY: logs
logs:
	journalctl -u panoptibot.service -f


.PHONY: start
start:
	sudo systemctl start panoptibot.service


.PHONY: stop
stop:
	sudo systemctl stop panoptibot.service


.PHONY: restart
restart:
	sudo systemctl restart panoptibot.service


.PHONY: status
status:
	sudo systemctl status panoptibot.service


.PHONY: install
install:
	bash install.sh


.PHONY: update
update:
	@if [ -n "$$(git status --porcelain)" ]; then \
		git stash; \
	fi
	git pull
	@if [ -n "$$(git stash list)" ]; then \
		git stash pop; \
	fi
	$(MAKE) install
