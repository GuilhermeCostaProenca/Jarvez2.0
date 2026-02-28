"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OutOfGameContext = void 0;
const Context_1 = require("./Context");
class OutOfGameContext extends Context_1.Context {
    constructor() {
        super(...arguments);
        this.sheet = undefined;
        this.activateContextualModifiers = false;
    }
    getCurrentLocation() {
        return undefined;
    }
}
exports.OutOfGameContext = OutOfGameContext;
