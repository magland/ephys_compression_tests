import { Range } from "./WorkerTypes";

// State Type
export interface TimeseriesViewState {
  selectedIndex: number;
  isDragging: boolean;
  lastDragX: number;
  xRange: Range;
}

// Initial State
export const initialState: TimeseriesViewState = {
  selectedIndex: -1,
  isDragging: false,
  lastDragX: 0,
  xRange: { min: 0, max: 999 },
};

// Action Types Union
type TimeseriesViewAction =
  | { type: "SET_SELECTED_INDEX"; index: number }
  | { type: "SET_IS_DRAGGING"; isDragging: boolean }
  | { type: "SET_LAST_DRAG_X"; x: number }
  | { type: "SET_X_RANGE"; range: Range };

// Reducer
export const timeseriesViewReducer = (
  state: TimeseriesViewState = initialState,
  action: TimeseriesViewAction,
): TimeseriesViewState => {
  switch (action.type) {
    case "SET_SELECTED_INDEX":
      return {
        ...state,
        selectedIndex: action.index,
      };
    case "SET_IS_DRAGGING":
      return {
        ...state,
        isDragging: action.isDragging,
      };
    case "SET_LAST_DRAG_X":
      return {
        ...state,
        lastDragX: action.x,
      };
    case "SET_X_RANGE":
      return {
        ...state,
        xRange: action.range,
      };
    default:
      return state;
  }
};
