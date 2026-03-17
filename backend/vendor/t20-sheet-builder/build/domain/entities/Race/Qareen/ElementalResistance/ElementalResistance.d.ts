import { type AbilityEffectsInterface } from '../../../Ability';
import { RaceAbility } from '../../RaceAbility';
import { type QareenElementalResistanceType } from '../QareenElementalResistanceType';
import { type QareenType } from '../QareenType';
export declare class ElementalResistance extends RaceAbility {
    static qareenTypeToResistance: Record<QareenType, QareenElementalResistanceType>;
    effects: AbilityEffectsInterface;
    constructor(qareenType: QareenType);
}
