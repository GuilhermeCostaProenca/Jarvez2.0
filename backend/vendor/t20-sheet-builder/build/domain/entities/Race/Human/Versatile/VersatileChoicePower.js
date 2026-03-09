"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VersatileChoicePower = void 0;
const PickGeneralPower_1 = require("../../../Action/PickGeneralPower");
const VersatileChoice_1 = require("./VersatileChoice");
class VersatileChoicePower extends VersatileChoice_1.VersatileChoice {
    constructor(power) {
        super(power.name, 'power');
        this.power = power;
        this.name = power.name;
    }
    addToSheet(transaction, source) {
        transaction.run(new PickGeneralPower_1.PickGeneralPower({
            payload: {
                power: this.power,
                source,
            },
            transaction,
        }));
    }
    serialize() {
        return {
            name: this.name,
            type: 'power',
        };
    }
}
exports.VersatileChoicePower = VersatileChoicePower;
