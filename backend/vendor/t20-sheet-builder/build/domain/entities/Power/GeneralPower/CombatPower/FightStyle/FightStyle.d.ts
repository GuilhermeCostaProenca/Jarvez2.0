import { type CharacterAppliedFightStyle } from '../../../../Character/CharacterAppliedFightStyle';
import { type CharacterModifiers } from '../../../../Character/CharacterModifiers';
import { GeneralPower } from '../../GeneralPower';
import { GeneralPowerGroup } from '../../GeneralPowerGroup';
export declare abstract class FightStyle extends GeneralPower {
    group: GeneralPowerGroup;
    abstract applyModifiers(modifiers: CharacterModifiers): CharacterAppliedFightStyle;
}
