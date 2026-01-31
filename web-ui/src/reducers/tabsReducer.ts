export type TabAction =
  | { type: "ADD_TAB"; payload: { id: string; label: string; route: string } }
  | { type: "SET_ACTIVE_TAB"; payload: string }
  | { type: "CLOSE_TAB"; payload: string }
  | { type: "REORDER_TABS"; payload: { fromIndex: number; toIndex: number } };

export interface TabItem {
  id: string;
  label: string;
  route: string;
}

export interface TabsState {
  tabs: TabItem[];
  activeTabId: string;
}

const initialState: TabsState = {
  tabs: [
    { id: "datasets", label: "Datasets", route: "/datasets" },
    { id: "algorithms", label: "Algorithms", route: "/algorithms" },
  ],
  activeTabId: "datasets",
};

export function tabsReducer(
  state: TabsState = initialState,
  action: TabAction,
): TabsState {
  switch (action.type) {
    case "ADD_TAB": {
      // If tab already exists, just set it as active
      if (state.tabs.some((tab) => tab.id === action.payload.id)) {
        return {
          ...state,
          activeTabId: action.payload.id,
        };
      }

      // Otherwise add new tab
      return {
        ...state,
        tabs: [...state.tabs, action.payload],
        activeTabId: action.payload.id,
      };
    }
    case "SET_ACTIVE_TAB":
      return {
        ...state,
        activeTabId: action.payload,
      };
    case "REORDER_TABS": {
      const newTabs = [...state.tabs];
      const [movedTab] = newTabs.splice(action.payload.fromIndex, 1);
      newTabs.splice(action.payload.toIndex, 0, movedTab);
      return {
        ...state,
        tabs: newTabs,
      };
    }
    case "CLOSE_TAB": {
      // Don't allow closing of datasets or algorithms tabs
      if (action.payload === "datasets" || action.payload === "algorithms") {
        return state;
      }

      const newTabs = state.tabs.filter((tab) => tab.id !== action.payload);

      // If we're closing the active tab, activate the last tab in the list
      if (state.activeTabId === action.payload) {
        return {
          tabs: newTabs,
          activeTabId: newTabs[newTabs.length - 1].id,
        };
      }

      return {
        ...state,
        tabs: newTabs,
      };
    }
    default:
      return state;
  }
}
