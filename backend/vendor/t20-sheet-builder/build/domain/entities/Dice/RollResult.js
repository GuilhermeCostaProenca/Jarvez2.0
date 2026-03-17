"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RollResult = void 0;
class RollResult {
    constructor(params) {
        this.total = params.total;
        this.rolls = params.rolls;
        this.discartedRolls = params.discartedRolls;
    }
    append(rollResult) {
        this.total += rollResult.total;
        this.rolls.push(...rollResult.rolls);
        this.discartedRolls.push(...rollResult.discartedRolls);
    }
}
exports.RollResult = RollResult;
