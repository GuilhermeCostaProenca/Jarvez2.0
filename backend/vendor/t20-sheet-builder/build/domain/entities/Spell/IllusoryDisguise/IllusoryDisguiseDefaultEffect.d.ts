import type { EffectDuration, EffectRange } from '../../Ability/ActivateableAbilityEffect';
import type { Affectable } from '../../Affectable/Affectable';
import type { Cost } from '../../Sheet/CharacterSheet/CharacterSheetInterface';
import { SpellEffect } from '../SpellEffect';
export declare class IllusoryDisguiseDefaultEffect extends SpellEffect {
    baseCosts: Cost[];
    description: string;
    static get duration(): EffectDuration;
    static get modifierValue(): number;
    affectable: Affectable;
    range: EffectRange;
    constructor();
}
