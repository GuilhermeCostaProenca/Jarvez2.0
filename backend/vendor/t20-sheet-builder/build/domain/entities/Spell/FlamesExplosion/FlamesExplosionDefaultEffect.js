"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlamesExplosionDefaultEffect = void 0;
const EffectAffectable_1 = require("../../Ability/EffectAffectable");
const ManaCost_1 = require("../../ManaCost");
const SpellEffect_1 = require("../SpellEffect");
const SpellName_1 = require("../SpellName");
class FlamesExplosionDefaultEffect extends SpellEffect_1.SpellEffect {
    constructor() {
        super({
            duration: 'immediate',
            execution: 'default',
            source: SpellName_1.SpellName.flamesExplosion,
        });
        this.description = 'Um leque de chamas irrompe de suas'
            + ' mãos, causando 2d6 pontos de dano de'
            + ' fogo às criaturas na área.';
        this.affectable = new EffectAffectable_1.EffectAffectableArea('cone');
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.range = 'personal';
    }
}
exports.FlamesExplosionDefaultEffect = FlamesExplosionDefaultEffect;
