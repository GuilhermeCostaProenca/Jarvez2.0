"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RolePower = void 0;
const Power_1 = require("../Power/Power");
class RolePower extends Power_1.Power {
    constructor(name) {
        super(name, 'role');
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
exports.RolePower = RolePower;
