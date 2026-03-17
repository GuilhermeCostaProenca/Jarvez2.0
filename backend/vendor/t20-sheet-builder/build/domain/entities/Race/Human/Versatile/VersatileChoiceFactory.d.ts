import { GeneralPowerName } from '../../../Power';
import { SkillName } from '../../../Skill';
import { type VersatileChoice, type VersatileChoiceType } from './VersatileChoice';
export declare class VersatileChoiceFactory {
    static make(type: VersatileChoiceType, choice: SkillName | GeneralPowerName): VersatileChoice;
    private static makeVersatileChoiceSkill;
    private static makeVersatileChoicePower;
    private static isPower;
    private static isSkill;
}
