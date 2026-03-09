"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PreviewContext = void 0;
const Context_1 = require("./Context");
class PreviewContext extends Context_1.Context {
    constructor(sheet) {
        super();
        this.sheet = sheet;
        this.activateContextualModifiers = true;
    }
    getCurrentLocation() {
        return undefined;
    }
}
exports.PreviewContext = PreviewContext;
