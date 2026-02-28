"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InGameContextFake = void 0;
const Context_1 = require("./Context");
class InGameContextFake extends Context_1.Context {
    constructor() {
        super(...arguments);
        this.activateContextualModifiers = true;
        this.location = {
            isUnderground: true,
        };
    }
    getCurrentLocation() {
        return this.location;
    }
}
exports.InGameContextFake = InGameContextFake;
