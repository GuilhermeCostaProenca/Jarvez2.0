"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DiceRoll = void 0;
const SheetBuilderError_1 = require("../../errors/SheetBuilderError");
const RollResult_1 = require("./RollResult");
class DiceRoll {
    constructor(diceQuantity, diceSides, discardLowestDiceQty = 0) {
        this.diceQuantity = diceQuantity;
        this.diceSides = diceSides;
        this.discardLowestDiceQty = discardLowestDiceQty;
        this.validateDiceQuantity(diceQuantity);
    }
    serialize() {
        return {
            diceQuantity: this.diceQuantity,
            diceSides: this.diceSides,
        };
    }
    roll(random) {
        const allResults = [];
        for (let i = 0; i < this.diceQuantity; i += 1) {
            allResults.push(random.get(1, this.diceSides));
        }
        allResults.sort((a, b) => a - b);
        const discartedRolls = allResults.filter((_, i) => i < this.discardLowestDiceQty);
        const rolls = allResults.filter((_, i) => i >= this.discardLowestDiceQty);
        const total = rolls.reduce((a, b) => a + b, 0);
        return new RollResult_1.RollResult({
            discartedRolls,
            rolls,
            total,
        });
    }
    validateDiceQuantity(diceQuantity) {
        if (diceQuantity < 1) {
            throw new SheetBuilderError_1.SheetBuilderError('INVALID_DICE_QUANTITY');
        }
    }
}
exports.DiceRoll = DiceRoll;
