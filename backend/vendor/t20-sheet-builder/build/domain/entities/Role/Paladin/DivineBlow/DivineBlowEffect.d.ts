import { TriggeredEffect, type TriggeredEffectDisableParams, type TriggeredEffectEnableParams, type TriggeredEffectEnableReturn } from '../../../Ability';
import { type TriggeredEffectActivation } from '../../../Ability/TriggeredEffectActivation';
import { type Cost } from '../../../Sheet';
export declare class DivineBlowEffect extends TriggeredEffect {
    baseCosts: Cost[];
    description: string;
    constructor();
    enable({ modifiersIndexes, modifiers }: TriggeredEffectEnableParams, activation: TriggeredEffectActivation): TriggeredEffectEnableReturn;
    disable({ modifiersIndexes, modifiers }: TriggeredEffectDisableParams): void;
}
