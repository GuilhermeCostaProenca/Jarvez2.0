import { type AbilityEffectStatic } from './AbilityEffectStatic';
export declare class AbilityEffectsStatic {
    passive: Record<string, AbilityEffectStatic>;
    triggered: Record<string, AbilityEffectStatic>;
    activateable: Record<string, AbilityEffectStatic>;
    roleplay: Record<string, AbilityEffectStatic>;
    constructor(params?: {
        passive?: Record<string, AbilityEffectStatic>;
        triggered?: Record<string, AbilityEffectStatic>;
        activateable?: Record<string, AbilityEffectStatic>;
        roleplay?: Record<string, AbilityEffectStatic>;
    });
}
