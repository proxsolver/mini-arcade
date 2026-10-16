/* Mini Arcade 리더보드 클라이언트 — 모든 게임이 공용으로 사용 */
(function () {
  const GAME_META = {
    battle:    { label: '🔢 2048 대결',   metric: '점수',        better: 'high' },
    connect4:  { label: '🔴 사목',        metric: '승리 시 착수 수', better: 'low'  },
    othello:   { label: '⚪ 오셀로',      metric: '내 돌 수',     better: 'high' },
    memory:    { label: '💾 짝맞추기',    metric: '가져온 짝',    better: 'high' },
    tictactoe: { label: '⭕ 틱택토',      metric: '승리 시 내 착수 수', better: 'low' },
    rps:       { label: '✌️ 가위바위보',  metric: '득점 차',      better: 'high' },
    reaction:  { label: '⚡ 반응속도',    metric: '평균 반응(ms)', better: 'low'  },
    mole:      { label: '🔨 두더지잡기',  metric: '잡은 두더지',  better: 'high' },
    baseball:  { label: '⚾ 숫자야구',    metric: '정답 시도 수', better: 'low'  },
  };

  window.LB = {
    meta: GAME_META,
    name() {
      try { return localStorage.getItem('arcade_player') || '익명'; } catch (e) { return '익명'; }
    },
    async submit(game, result, score, cpu) {
      try {
        await fetch('/api/score', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game, player: LB.name(), result, score, cpu: cpu || '?' }),
        });
      } catch (e) { /* 오프라인(예: GitHub Pages)이면 조용히 무시 */ }
    },
  };
})();
