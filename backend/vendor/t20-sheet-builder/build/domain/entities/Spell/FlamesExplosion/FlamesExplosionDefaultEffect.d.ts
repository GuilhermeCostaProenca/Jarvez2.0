import type { EffectRange } from '../../Ability/ActivateableAbilityEffect';
import type { Affectable } from '../../Affectable/Affectable';
import type { Cost } from '../../Sheet/CharacterSheet/CharacterSheetInterface';
import { SpellEffect } from '../SpellEffect';
export declare class FlamesExplosionDefaultEffect extends SpellEffect {
    description: string;
    affectable: Affectable;
    baseCosts: Cost[];
    range: EffectRange;
    constructor();
}
