import { type AbilityEffectsInterface } from '../../../../../../Ability/AbilityEffects';
import { type AbilityLevel } from '../../../../../../Ability/AbilityLevel';
import { type TormentaPower } from '../../../../../../Power/GeneralPower/TormentaPower/TormentaPower';
import { type Attribute } from '../../../../../../Sheet';
import { type SerializedArcanistLineage } from '../../../../SerializedArcanist';
import { ArcanistLineage } from '../ArcanistLineage';
import { ArcanistLineageType } from '../ArcanistLineageType';
import { ArcanistLineageRedCustomTormentaPowersAttributeEffect } from './ArcanistLineageRedCustomTormentaPowersAttributeEffect';
import { ArcanistLineageRedExtraTormentaPowerEffect } from './ArcanistLineageRedExtraTormentaPowerEffect';
export declare class ArcanistLineageRed extends ArcanistLineage {
    readonly attributeToLose: Attribute;
    readonly type = ArcanistLineageType.red;
    effects: Record<AbilityLevel, AbilityEffectsInterface> & {
        basic: {
            passive: {
                customTormentaPowersAttribute: ArcanistLineageRedCustomTormentaPowersAttributeEffect;
                extraTormentaPower: ArcanistLineageRedExtraTormentaPowerEffect;
            };
        };
    };
    constructor(power: TormentaPower, attributeToLose?: Attribute);
    getExtraPower(): TormentaPower;
    getCustomTormentaPowersAttribute(): Attribute;
    serialize(): SerializedArcanistLineage;
}
