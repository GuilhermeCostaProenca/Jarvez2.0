"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FixedModifiersListFake = void 0;
const vitest_1 = require("vitest");
class FixedModifiersListFake {
    constructor() {
        this.get = vitest_1.vi.fn();
        this.modifiers = [];
        this.total = 0;
        this.add = vitest_1.vi.fn();
        this.remove = vitest_1.vi.fn();
        this.serialize = vitest_1.vi.fn();
    }
    getTotal() {
        return this.total;
    }
}
exports.FixedModifiersListFake = FixedModifiersListFake;
