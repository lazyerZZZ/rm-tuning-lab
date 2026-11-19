#!/usr/bin/env bash
# Run inside an X display after sourcing the built workspace.
set -eo pipefail
log=$(mktemp)
ros2 launch rm_tuning_lab lesson.launch.py >"$log" 2>&1 &
launcher=$!
finish() {
  kill -INT "$launcher" 2>/dev/null || true
  cat "$log"
  rm -f "$log"
}
trap finish EXIT
for _ in {1..40}; do
  sleep 1
  titles=$(xdotool search --onlyvisible --name '.+' getwindowname %@ 2>/dev/null || true)
  if [[ "$titles" == *"LessonPlot"* && "$titles" == *"rqt_reconfigure"* ]] &&
      ros2 topic info /tuning_lab/output | grep -Eq 'Subscription count: [1-9]' &&
      ros2 topic info /tuning_lab/reference | grep -Eq 'Subscription count: [1-9]'; then
    printf '%s\n' "$titles"
    python3 tests/ros/editor.py
    exit 0
  fi
  kill -0 "$launcher" || exit 1
done
echo "Expected two rqt windows and live subscriptions, saw: $titles" >&2
exit 1
