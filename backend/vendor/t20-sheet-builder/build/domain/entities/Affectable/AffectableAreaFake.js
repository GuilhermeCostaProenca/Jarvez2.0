"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AffectableAreaFake = void 0;
const AffectableArea_1 = require("./AffectableArea");
const AffectableTargetCreatureFake_1 = require("./AffectableTargetCreatureFake");
class AffectableAreaFake extends AffectableArea_1.AffectableArea {
    constructor() {
        super('cone');
        const firstCreature = new AffectableTargetCreatureFake_1.AffectableTargetCreatureFake();
        const secondCreature = new AffectableTargetCreatureFake_1.AffectableTargetCreatureFake();
        secondCreature.resisted = true;
        this.creaturesInside = [firstCreature, secondCreature];
    }
    getCreaturesInside() {
        return this.creaturesInside;
    }
}
exports.AffectableAreaFake = AffectableAreaFake;
