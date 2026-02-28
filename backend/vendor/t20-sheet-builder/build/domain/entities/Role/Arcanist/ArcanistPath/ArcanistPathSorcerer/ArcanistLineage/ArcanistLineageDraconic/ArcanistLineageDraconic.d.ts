import { type AbilityEffectsInterface } from '../../../../../../Ability/AbilityEffects';
import { type AbilityLevel } from '../../../../../../Ability/AbilityLevel';
import { type SerializedArcanistLineage } from '../../../../SerializedArcanist';
import { ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageType } from '../ArcanistLineageType';
import { ArcanistLineageDraconicCharismaBonusEffect } from './ArcanistLineageDraconicCharismaBonusEffect';
import { ArcanistLineageDraconicDamageReductionEffect } from './ArcanistLineageDraconicDamageReductionEffect';
import { type ArcanistLineageDraconicDamageType } from './ArcanistLineageDraconicDamageType';
export declare class ArcanistLineageDraconic extends ArcanistLineage {
    effects: Record<AbilityLevel, AbilityEffectsInterface> & {
        basic: {
            passive: {
                charismaBonus: ArcanistLineageDraconicCharismaBonusEffect;
                damageReduction: ArcanistLineageDraconicDamageReductionEffect;
            };
        };
    };
    readonly type = ArcanistLineageType.draconic;
    constructor(damageType: ArcanistLineageDraconicDamageType);
    getDamageType(): ArcanistLineageDraconicDamageType;
    serialize(): SerializedArcanistLineage;
}
