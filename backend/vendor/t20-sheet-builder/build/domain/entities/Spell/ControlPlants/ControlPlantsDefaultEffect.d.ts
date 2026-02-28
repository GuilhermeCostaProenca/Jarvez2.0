import { type EffectRange } from '../../Ability';
import { type Affectable } from '../../Affectable/Affectable';
import type { Cost } from '../../Sheet/CharacterSheet/CharacterSheetInterface';
import { SpellEffect } from '../SpellEffect';
export declare class ControlPlantsDefaultEffect extends SpellEffect {
    range: EffectRange;
    affectable: Affectable;
    baseCosts: Cost[];
    description: string;
    constructor();
}
