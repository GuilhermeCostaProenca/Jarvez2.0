"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GrantedPower = void 0;
const Power_1 = require("../Power");
class GrantedPower extends Power_1.Power {
    constructor(name) {
        super(name, 'granted');
        this.name = name;
    }
    serialize() {
        return {
            name: this.name,
            abilityType: this.abilityType,
            effects: this.effects.serialize(),
        };
    }
}
exports.GrantedPower = GrantedPower;
