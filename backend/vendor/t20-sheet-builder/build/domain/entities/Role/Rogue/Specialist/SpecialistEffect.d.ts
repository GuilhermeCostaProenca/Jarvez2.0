import { TriggeredEffect, type TriggeredEffectDisableParams, type TriggeredEffectEnableParams } from '../../../Ability';
import { type SpecialistActivation } from '../../../Ability/TriggeredEffectActivation';
import { ManaCost } from '../../../ManaCost';
import { type Cost } from '../../../Sheet';
import { type SkillName } from '../../../Skill';
export declare class SpecialistEffect extends TriggeredEffect {
    readonly baseCosts: Cost[];
    description: string;
    private readonly skills;
    constructor(skills: Set<SkillName>);
    getSkills(): SkillName[];
    enable({ modifiersIndexes, modifiers }: TriggeredEffectEnableParams, activation: SpecialistActivation): {
        manaCost?: ManaCost | undefined;
    };
    disable({ modifiersIndexes, modifiers }: TriggeredEffectDisableParams): void;
}
