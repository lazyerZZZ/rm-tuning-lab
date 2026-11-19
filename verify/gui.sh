set -eo pipefail
cd "$HOME"
source /opt/ros/jazzy/setup.bash
source ~/rm_ws/install/setup.bash
mkdir -p evidence
export PYTHONPATH="$HOME/check:$PYTHONPATH"
ros2 launch rm_tuning_lab lesson.launch.py case_id:=wheel_step >evidence/launch.log 2>&1 &
launch_pid=$!
trap 'kill -INT "$launch_pid" || true' EXIT
for stage in select p1 p3 pi; do
    echo "$stage" > evidence/next
    mv evidence/next evidence/request
    for _ in {1..60}; do
        if [[ -f evidence/error ]]; then cat evidence/error; exit 1; fi
        if [[ -f evidence/done-$stage ]]; then break; fi
        sleep 1
    done
    if [[ ! -f evidence/done-$stage ]]; then cat evidence/launch.log; exit 1; fi
    if [[ "$stage" != select ]]; then
        for _ in {1..20}; do
            if ros2 node list | grep -Fx /tuning_lab; then break; fi
            sleep 1
        done
        ros2 param get /tuning_lab kp
        ros2 param get /tuning_lab ki
        python3 check/measure.py "$stage"
    fi
done
