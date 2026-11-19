set -eo pipefail
mkdir evidence
export EVIDENCE="$PWD/evidence"
export PYTHONPATH="$PWD/verify:$PYTHONPATH"
ros2 launch rm_tuning_lab lesson.launch.py case_id:="$LESSON" >evidence/launch.log 2>&1 &
launch_pid=$!
trap 'kill -INT "$launch_pid" || true; cat evidence/launch.log' EXIT
if [[ "$LESSON" != range_step ]]; then
    ros2 run rqt_plot rqt_plot -e >evidence/extra-plot.log 2>&1 &
fi
stages=$(python3 -c 'import os; from stages import STAGES; print(" ".join(STAGES[os.environ["LESSON"]]))')
for stage in select $stages; do
    echo "$stage" > evidence/next
    mv evidence/next evidence/request
    for _ in {1..60}; do
        if [[ -f evidence/error ]]; then cat evidence/error; exit 1; fi
        if [[ -f evidence/done-$stage ]]; then break; fi
        sleep 1
    done
    test -f evidence/done-$stage
    if [[ "$stage" != select ]]; then
        python3 tools/score_trial.py --csv "evidence/$stage.csv" | tee "evidence/$stage.txt"
    fi
done
for _ in {1..30}; do test ! -f evidence/plots-ready || break; sleep 1; done
test -f evidence/plots-ready
touch evidence/capture
for _ in {1..10}; do test ! -f evidence/captured || break; sleep 1; done
test -s evidence/rqt-plot.png
grep -F '最终验收：通过' "evidence/$stage.txt"
