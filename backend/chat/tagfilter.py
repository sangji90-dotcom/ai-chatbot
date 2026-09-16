"""스트리밍 중 태그 누출 방지.

응답 끝에 `[EMOTION:happy] [SITUATION:cafe]` 가 붙는데, 청크 단위로 그대로
흘려보내면 유저 화면에 태그가 그대로 찍힌다. 그렇다고 완성될 때까지 기다리면
스트리밍의 의미가 없다.

'[' 를 만나면 그 지점부터 보류하고, 태그로 확정되면 버리고 아니면 다시 내보낸다.
"""
import re

TAG_RE = re.compile(r"\[(?:EMOTION|SITUATION):\w+\]\s*")
# 태그가 되다 만 상태인지 판정 (예: "[EMO", "[EMOTION:ha")
PARTIAL_RE = re.compile(r"\[(?:E(?:M(?:O(?:T(?:I(?:O(?:N(?::\w*)?)?)?)?)?)?)?|S(?:I(?:T(?:U(?:A(?:T(?:I(?:O(?:N(?::\w*)?)?)?)?)?)?)?)?)?)?$")


class TagStripper:
    """feed() 로 청크를 넣고, 내보내도 안전한 부분만 돌려받는다."""

    def __init__(self) -> None:
        self._pending = ""
        self.raw = ""

    def feed(self, chunk: str) -> str:
        self.raw += chunk
        buf = self._pending + chunk

        # 완성된 태그는 제거
        buf = TAG_RE.sub("", buf)

        # 끝부분이 태그가 되다 만 상태면 보류
        m = PARTIAL_RE.search(buf)
        if m and m.start() < len(buf):
            self._pending = buf[m.start():]
            return buf[: m.start()]

        self._pending = ""
        return buf

    def flush(self) -> str:
        """스트림 종료 시 남은 보류분에서 태그를 걷어내고 반환."""
        rest = TAG_RE.sub("", self._pending)
        self._pending = ""
        return rest

    def tags(self) -> tuple[str, str]:
        emotion = re.search(r"\[EMOTION:(\w+)\]", self.raw)
        situation = re.search(r"\[SITUATION:(\w+)\]", self.raw)
        return (emotion.group(1) if emotion else "neutral",
                situation.group(1) if situation else "default")

    def clean_text(self) -> str:
        return TAG_RE.sub("", self.raw).strip()
