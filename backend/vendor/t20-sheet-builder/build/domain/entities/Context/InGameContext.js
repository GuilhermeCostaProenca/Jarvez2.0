"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InGameContext = void 0;
const Context_1 = require("./Context");
class InGameContext extends Context_1.Context {
    constructor(initialLocation, sheet) {
        super();
        this.sheet = sheet;
        this.activateContextualModifiers = true;
        this.location = initialLocation;
    }
    getCurrentLocation() {
        return this.location;
    }
}
exports.InGameContext = InGameContext;
