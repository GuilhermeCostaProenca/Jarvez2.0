"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TormentaPower = void 0;
const DecreaseAttribute_1 = require("../../../Action/DecreaseAttribute");
const GeneralPower_1 = require("../GeneralPower");
const GeneralPowerGroup_1 = require("../GeneralPowerGroup");
class TormentaPower extends GeneralPower_1.GeneralPower {
    constructor() {
        super(...arguments);
        this.group = GeneralPowerGroup_1.GeneralPowerGroup.tormenta;
    }
    addToSheet(transaction) {
        super.addToSheet(transaction);
        transaction.run(new DecreaseAttribute_1.DecreaseAttribute({
            payload: {
                attribute: transaction.sheet.getSheetAttributes().getTormentaPowersAttribute(),
                quantity: 1,
                source: this.name,
            },
            transaction,
        }));
    }
}
exports.TormentaPower = TormentaPower;
