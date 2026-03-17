"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RaceFake = void 0;
const vitest_1 = require("vitest");
const RaceName_1 = require("./RaceName");
class RaceFake {
    constructor() {
        this.serialize = vitest_1.vi.fn();
        this.abilities = {};
        this.name = RaceName_1.RaceName.human;
        this.attributeModifiers = {};
        this.applyAbilities = vitest_1.vi.fn();
        this.applyAttributesModifiers = vitest_1.vi.fn((attributes) => attributes);
        this.addToSheet = vitest_1.vi.fn();
    }
}
exports.RaceFake = RaceFake;
