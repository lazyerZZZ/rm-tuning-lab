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
    plot_window=$(xdotool search --onlyvisible --name 'LessonPlot' | head -1)
    xdotool windowsize --sync "$plot_window" 900 520
    xdotool windowmove "$plot_window" 0 0
    xdotool windowraise "$plot_window"
    ros2 service call /tuning_lab/reset std_srvs/srv/Trigger '{}' >/dev/null
    sleep 6
    python3 tests/ros/capture.py "$plot_window"
    exit 0
  fi
  kill -0 "$launcher" || exit 1
done
echo "Expected two rqt windows and live subscriptions, saw: $titles" >&2
exit 1
