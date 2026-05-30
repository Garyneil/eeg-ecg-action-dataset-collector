"""Action protocol definition for EEG/ECG dataset collection."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Action:
    """Single action definition."""

    action_id: int
    name: str
    zh_name: str
    description: str


DEFAULT_ACTIONS: List[Action] = [
    Action(0, "rest", "静息", "Baseline resting state."),
    Action(1, "left_hand_raise", "左手抬起", "Raise the left hand."),
    Action(2, "right_hand_raise", "右手抬起", "Raise the right hand."),
    Action(3, "both_hands_raise", "双手抬起", "Raise both hands."),
    Action(4, "left_hand_grasp", "左手抓握", "Grasp with the left hand."),
    Action(5, "right_hand_grasp", "右手抓握", "Grasp with the right hand."),
    Action(6, "left_arm_reach", "左臂前伸", "Reach forward with the left arm."),
    Action(7, "right_arm_reach", "右臂前伸", "Reach forward with the right arm."),
    Action(8, "head_turn_left", "头向左转", "Turn the head to the left."),
    Action(9, "head_turn_right", "头向右转", "Turn the head to the right."),
    Action(10, "walk_forward", "向前走", "Walk forward."),
    Action(11, "stop", "停止", "Stop movement."),
]


def get_actions() -> List[Action]:
    """Return the default 12-class action protocol."""
    return DEFAULT_ACTIONS
