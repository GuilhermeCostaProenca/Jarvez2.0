"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PassiveEffect = void 0;
const AbilityEffect_1 = require("./AbilityEffect");
class PassiveEffect extends AbilityEffect_1.AbilityEffect {
    constructor(source) {
        super('passive', source);
    }
}
exports.PassiveEffect = PassiveEffect;
