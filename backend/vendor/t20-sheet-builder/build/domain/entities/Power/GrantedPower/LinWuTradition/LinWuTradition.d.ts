import { AbilityEffects } from '../../../Ability';
import { AbilityEffectsStatic } from '../../../Ability/AbilityEffectsStatic';
import { GrantedPower } from '../GrantedPower';
import { GrantedPowerName } from '../GrantedPowerName';
import { LinWuTraditionEffect } from './LinWuTraditionEffect';
export declare class LiWuTradition extends GrantedPower {
    static readonly powerName = GrantedPowerName.linWuTradition;
    static readonly effects: AbilityEffectsStatic;
    effects: AbilityEffects<{
        roleplay: {
            default: LinWuTraditionEffect;
        };
    }>;
    constructor();
}
