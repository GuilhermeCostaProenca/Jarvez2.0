"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ContextualModifiersListFake = void 0;
const vitest_1 = require("vitest");
class ContextualModifiersListFake {
    constructor() {
        this.serialize = vitest_1.vi.fn();
        this.get = vitest_1.vi.fn();
        this.modifiers = [];
        this.total = 0;
        this.maxTotal = 0;
        this.add = vitest_1.vi.fn();
        this.remove = vitest_1.vi.fn();
    }
    getTotal() {
        return this.total;
    }
    getMaxTotal() {
        return this.maxTotal;
    }
}
exports.ContextualModifiersListFake = ContextualModifiersListFake;
