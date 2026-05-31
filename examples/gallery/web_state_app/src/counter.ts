export type CounterState = { count: number; message: string };
export type Action = { type: "increment" };

export function reduceCounter(state: CounterState, action: Action): CounterState {
  if (action.type === "increment") {
    return { ...state, count: state.count + 1 };
  }
  return state;
}

export async function loadMessage(state: CounterState): Promise<CounterState> {
  return { ...state, message: `Count is ${state.count}` };
}

export function renderCounter(state: CounterState): string {
  return `<button>Increment</button><output>${state.message}</output>`;
}

export async function onIncrement(state: CounterState): Promise<string> {
  const updated = reduceCounter(state, { type: "increment" });
  const withMessage = await loadMessage(updated);
  return renderCounter(withMessage);
}
