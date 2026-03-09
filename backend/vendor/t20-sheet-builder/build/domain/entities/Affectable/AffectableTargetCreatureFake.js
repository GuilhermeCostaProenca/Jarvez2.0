"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AffectableTargetCreatureFake = void 0;
const AffectableTarget_1 = require("./AffectableTarget");
const vitest_1 = require("vitest");
class AffectableTargetCreatureFake extends AffectableTarget_1.AffectableTargetCreature {
    constructor() {
        super(...arguments);
        this.resisted = false;
        this.receiveDamage = vitest_1.vi.fn();
        this.setCondition = vitest_1.vi.fn();
    }
    resist() {
        return this.resisted;
    }
}
exports.AffectableTargetCreatureFake = AffectableTargetCreatureFake;
