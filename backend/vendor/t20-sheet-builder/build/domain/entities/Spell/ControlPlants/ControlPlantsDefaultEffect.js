"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ControlPlantsDefaultEffect = void 0;
const EffectAffectable_1 = require("../../Ability/EffectAffectable");
const ManaCost_1 = require("../../ManaCost");
const SpellEffect_1 = require("../SpellEffect");
const SpellName_1 = require("../SpellName");
class ControlPlantsDefaultEffect extends SpellEffect_1.SpellEffect {
    constructor() {
        super({
            duration: 'scene',
            execution: 'default',
            source: SpellName_1.SpellName.controlPlants,
        });
        this.range = 'short';
        this.affectable = new EffectAffectable_1.EffectAffectableArea('square');
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Esta magia só pode ser lançada em'
            + ' uma área com vegetação. As plantas se enroscam nas criaturas da área.'
            + ' Aquelas que falharem na resistência ficam enredadas. Uma vítima pode'
            + ' se libertar com uma ação padrão e um teste de Acrobacia ou Atletismo.'
            + ' Além disso, a área é considerada terreno difícil. No início de seus turnos,'
            + ' a vegetação tenta enredar novamente qualquer criatura na área, exigindo'
            + ' um novo teste de Reflexos.';
    }
}
exports.ControlPlantsDefaultEffect = ControlPlantsDefaultEffect;
