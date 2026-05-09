#!/usr/bin/env bash
# Expand env vars ($HOME, ${USER}, ...) in settings.json. Undefined vars left as-is.
perl -i.bak -pe \
  's/\$\{(\w+)\}/defined $ENV{$1} ? $ENV{$1} : $&/ge;
   s/\$(\w+)/defined $ENV{$1} ? $ENV{$1} : $&/ge' \
  ~/.claude/settings.json
