import type { EffectDuration, EffectRange } from '../../Ability/ActivateableAbilityEffect';
import { AffectableTarget } from '../../Affectable/AffectableTarget';
import { ManaCost } from '../../ManaCost';
import { SpellEffect } from '../SpellEffect';
export declare class ArcaneArmorDefaultEffect extends SpellEffect {
    description: string;
    static get defenseBonus(): number;
    static get duration(): EffectDuration;
    affectable: AffectableTarget;
    baseCosts: ManaCost[];
    range: EffectRange;
    constructor();
}
