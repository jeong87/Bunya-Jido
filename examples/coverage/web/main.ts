import { helper } from "./local";
import React from "react";

export function render(): string {
  return helper(String(React));
}
