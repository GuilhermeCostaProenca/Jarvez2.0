"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GeneralPower = void 0;
const Power_1 = require("../Power");
class GeneralPower extends Power_1.Power {
    constructor(name) {
        super(name, 'general');
        this.name = name;
    }
    serialize() {
        return {
            name: this.name,
            abilityType: this.abilityType,
            effects: this.effects.serialize(),
            group: this.group,
        };
    }
}
exports.GeneralPower = GeneralPower;
