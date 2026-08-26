import type { GraphData } from '../types'

export interface HeroGraph {
  id: string
  label: string
  description: string
  data: GraphData
}

export const LLM_LANDSCAPE: HeroGraph = {
  id: 'llm-landscape',
  label: 'LLM Landscape',
  description: 'Labs, models, and the techniques that power them — with temporal versioning showing what got superseded.',
  data: {
    nodes: [
      // Labs
      { id: 'openai', name: 'OpenAI', entity_type: 'organization', summary: 'AI safety company and GPT series creator', confidence: 1.0 },
      { id: 'anthropic', name: 'Anthropic', entity_type: 'organization', summary: 'AI safety company, founded by ex-OpenAI researchers. Creators of Claude.', confidence: 1.0 },
      { id: 'google', name: 'Google DeepMind', entity_type: 'organization', summary: 'Merged AI research division of Google, creators of Gemini', confidence: 1.0 },
      { id: 'meta', name: 'Meta AI', entity_type: 'organization', summary: 'Meta\'s AI research lab, open-sources Llama series', confidence: 1.0 },
      { id: 'mistral', name: 'Mistral AI', entity_type: 'organization', summary: 'French AI startup known for efficient open-weight models', confidence: 0.95 },
      // Models — current
      { id: 'gpt4o', name: 'GPT-4o', entity_type: 'tool', summary: 'OpenAI\'s flagship multimodal model. Superseded GPT-3.5 and GPT-4.', confidence: 1.0 },
      { id: 'claude35', name: 'Claude 3.5 Sonnet', entity_type: 'tool', summary: 'Anthropic\'s top coding and reasoning model, trained with Constitutional AI', confidence: 1.0 },
      { id: 'gemini15', name: 'Gemini 1.5 Pro', entity_type: 'tool', summary: 'Google\'s long-context multimodal model with 1M token context window', confidence: 1.0 },
      { id: 'llama3', name: 'Llama 3', entity_type: 'tool', summary: 'Meta\'s open-weight LLM series, widely used for fine-tuning', confidence: 1.0 },
      { id: 'mistral7b', name: 'Mistral 7B', entity_type: 'tool', summary: 'Efficient open-weight model that outperforms larger Llama 2 models', confidence: 0.95 },
      // Models — superseded (lower confidence to render smaller)
      { id: 'gpt35', name: 'GPT-3.5', entity_type: 'tool', summary: 'Previous OpenAI flagship. Widely used for ChatGPT. Now superseded by GPT-4o.', confidence: 0.4 },
      // Concepts
      { id: 'transformer', name: 'Transformer', entity_type: 'concept', summary: 'The attention-based neural architecture underpinning all modern LLMs', confidence: 1.0 },
      { id: 'rlhf', name: 'RLHF', entity_type: 'concept', summary: 'Reinforcement Learning from Human Feedback — aligns LLMs to human preferences', confidence: 0.95 },
      { id: 'cai', name: 'Constitutional AI', entity_type: 'concept', summary: 'Anthropic\'s technique for training helpful, harmless, honest models via self-critique', confidence: 0.95 },
      { id: 'rag', name: 'RAG', entity_type: 'concept', summary: 'Retrieval-Augmented Generation — grounds LLM responses with external knowledge', confidence: 0.9 },
      // People
      { id: 'dario', name: 'Dario Amodei', entity_type: 'person', summary: 'CEO of Anthropic. Previously VP of Research at OpenAI.', confidence: 0.95 },
      { id: 'sam', name: 'Sam Altman', entity_type: 'person', summary: 'CEO of OpenAI', confidence: 0.95 },
    ],
    edges: [
      // Releases — current
      { from_id: 'openai', to_id: 'gpt4o', rel_type: 'released', summary: 'OpenAI released GPT-4o in May 2024', confidence: 1.0, active: true },
      { from_id: 'anthropic', to_id: 'claude35', rel_type: 'released', summary: 'Anthropic released Claude 3.5 Sonnet in June 2024', confidence: 1.0, active: true },
      { from_id: 'google', to_id: 'gemini15', rel_type: 'released', summary: 'Google released Gemini 1.5 Pro in February 2024', confidence: 1.0, active: true },
      { from_id: 'meta', to_id: 'llama3', rel_type: 'released', summary: 'Meta released Llama 3 in April 2024', confidence: 1.0, active: true },
      { from_id: 'mistral', to_id: 'mistral7b', rel_type: 'released', summary: 'Mistral AI released Mistral 7B in September 2023', confidence: 0.95, active: true },
      // Superseded release (inactive)
      { from_id: 'openai', to_id: 'gpt35', rel_type: 'released', summary: 'OpenAI released GPT-3.5 in 2022. Now superseded by GPT-4o.', confidence: 0.4, active: false },
      // Temporal: supersedes
      { from_id: 'gpt4o', to_id: 'gpt35', rel_type: 'supersedes', summary: 'GPT-4o superseded GPT-3.5 as OpenAI\'s recommended model', confidence: 1.0, active: true },
      // Techniques
      { from_id: 'anthropic', to_id: 'cai', rel_type: 'works_on', summary: 'Anthropic developed Constitutional AI as their alignment technique', confidence: 1.0, active: true },
      { from_id: 'cai', to_id: 'claude35', rel_type: 'depends_on', summary: 'Claude is trained using Constitutional AI', confidence: 1.0, active: true },
      { from_id: 'rlhf', to_id: 'gpt4o', rel_type: 'depends_on', summary: 'GPT-4o training pipeline uses RLHF for alignment', confidence: 0.95, active: true },
      { from_id: 'openai', to_id: 'rlhf', rel_type: 'works_on', summary: 'OpenAI pioneered RLHF with InstructGPT research', confidence: 0.95, active: true },
      // All models depend on Transformer
      { from_id: 'gpt4o', to_id: 'transformer', rel_type: 'depends_on', summary: 'GPT-4o is built on the Transformer architecture', confidence: 1.0, active: true },
      { from_id: 'claude35', to_id: 'transformer', rel_type: 'depends_on', summary: 'Claude is built on the Transformer architecture', confidence: 1.0, active: true },
      { from_id: 'gemini15', to_id: 'transformer', rel_type: 'depends_on', summary: 'Gemini is built on the Transformer architecture', confidence: 1.0, active: true },
      { from_id: 'llama3', to_id: 'transformer', rel_type: 'depends_on', summary: 'Llama 3 is built on the Transformer architecture', confidence: 1.0, active: true },
      // RAG
      { from_id: 'rag', to_id: 'transformer', rel_type: 'related_to', summary: 'RAG augments Transformer-based LLMs with retrieval', confidence: 0.9, active: true },
      // People
      { from_id: 'sam', to_id: 'openai', rel_type: 'works_on', summary: 'Sam Altman is CEO of OpenAI', confidence: 1.0, active: true },
      { from_id: 'dario', to_id: 'anthropic', rel_type: 'works_on', summary: 'Dario Amodei is CEO and co-founder of Anthropic', confidence: 1.0, active: true },
      // Temporal: Dario previously worked at OpenAI (inactive)
      { from_id: 'dario', to_id: 'openai', rel_type: 'works_on', summary: 'Dario was VP of Research at OpenAI before founding Anthropic in 2021', confidence: 0.4, active: false },
    ],
  },
}

export const TRANSFORMER_ARCH: HeroGraph = {
  id: 'transformer-arch',
  label: 'Transformer Architecture',
  description: '"Attention Is All You Need" (2017) — the building blocks of every modern LLM.',
  data: {
    nodes: [
      // Core
      { id: 'transformer', name: 'Transformer', entity_type: 'concept', summary: 'Attention-based sequence model introduced in "Attention Is All You Need" (Vaswani et al., 2017)', confidence: 1.0 },
      { id: 'encoder', name: 'Encoder', entity_type: 'concept', summary: 'Stack of N identical layers that build contextual representations of the input', confidence: 1.0 },
      { id: 'decoder', name: 'Decoder', entity_type: 'concept', summary: 'Stack of N identical layers that generate output tokens autoregressively', confidence: 1.0 },
      // Attention
      { id: 'mha', name: 'Multi-Head Attention', entity_type: 'concept', summary: 'Runs h parallel attention heads then concatenates and projects their outputs', confidence: 1.0 },
      { id: 'self-attn', name: 'Self-Attention', entity_type: 'concept', summary: 'Q/K/V attention where Q, K, V all come from the same sequence', confidence: 1.0 },
      { id: 'cross-attn', name: 'Cross-Attention', entity_type: 'concept', summary: 'Decoder attends to encoder output — K and V come from the encoder', confidence: 0.95 },
      // Sub-layers
      { id: 'ffn', name: 'Feed-Forward Network', entity_type: 'concept', summary: 'Two-layer MLP applied position-wise after attention: FFN(x) = max(0, xW1+b1)W2+b2', confidence: 1.0 },
      { id: 'layer-norm', name: 'Layer Normalization', entity_type: 'concept', summary: 'Normalizes activations across feature dimension. Applied before (pre-norm) or after (post-norm) sub-layers', confidence: 1.0 },
      { id: 'residual', name: 'Residual Connection', entity_type: 'concept', summary: 'Skip connections x + Sublayer(x) that allow gradient flow through deep stacks', confidence: 1.0 },
      // Input/output
      { id: 'pos-enc', name: 'Positional Encoding', entity_type: 'concept', summary: 'Sine/cosine functions injected at embedding layer to encode sequence position', confidence: 1.0 },
      { id: 'embedding', name: 'Token Embedding', entity_type: 'concept', summary: 'Maps discrete token IDs to dense vectors in d_model-dimensional space', confidence: 1.0 },
      { id: 'softmax', name: 'Softmax Output', entity_type: 'concept', summary: 'Final linear + softmax that projects decoder output to vocab probability distribution', confidence: 0.95 },
      // Downstream model variants
      { id: 'bert', name: 'BERT', entity_type: 'tool', summary: 'Encoder-only Transformer pre-trained with masked language modeling and NSP', confidence: 0.95 },
      { id: 'gpt', name: 'GPT', entity_type: 'tool', summary: 'Decoder-only Transformer pre-trained with causal language modeling', confidence: 1.0 },
      { id: 't5', name: 'T5', entity_type: 'tool', summary: 'Encoder-decoder Transformer that frames all NLP tasks as text-to-text', confidence: 0.9 },
    ],
    edges: [
      // Structure
      { from_id: 'encoder', to_id: 'transformer', rel_type: 'part_of', summary: 'Encoder is one half of the Transformer', confidence: 1.0, active: true },
      { from_id: 'decoder', to_id: 'transformer', rel_type: 'part_of', summary: 'Decoder is the other half of the Transformer', confidence: 1.0, active: true },
      // Encoder sub-layers
      { from_id: 'mha', to_id: 'encoder', rel_type: 'part_of', summary: 'Each encoder layer contains a multi-head self-attention sub-layer', confidence: 1.0, active: true },
      { from_id: 'ffn', to_id: 'encoder', rel_type: 'part_of', summary: 'Each encoder layer contains a position-wise feed-forward sub-layer', confidence: 1.0, active: true },
      { from_id: 'layer-norm', to_id: 'encoder', rel_type: 'part_of', summary: 'Layer norm applied after each sub-layer in the encoder', confidence: 1.0, active: true },
      { from_id: 'residual', to_id: 'encoder', rel_type: 'part_of', summary: 'Residual connections wrap each sub-layer in the encoder', confidence: 1.0, active: true },
      // Decoder sub-layers
      { from_id: 'mha', to_id: 'decoder', rel_type: 'part_of', summary: 'Decoder has masked self-attention in its first sub-layer', confidence: 1.0, active: true },
      { from_id: 'cross-attn', to_id: 'decoder', rel_type: 'part_of', summary: 'Decoder\'s second sub-layer is cross-attention over encoder output', confidence: 0.95, active: true },
      { from_id: 'ffn', to_id: 'decoder', rel_type: 'part_of', summary: 'Each decoder layer also has a feed-forward sub-layer', confidence: 1.0, active: true },
      // Attention internals
      { from_id: 'self-attn', to_id: 'mha', rel_type: 'part_of', summary: 'Each attention head computes scaled dot-product self-attention', confidence: 1.0, active: true },
      { from_id: 'cross-attn', to_id: 'mha', rel_type: 'related_to', summary: 'Cross-attention is the same mechanism as self-attention but with mixed Q/K/V sources', confidence: 0.9, active: true },
      // Inputs
      { from_id: 'embedding', to_id: 'transformer', rel_type: 'part_of', summary: 'Token embeddings form the input to both encoder and decoder', confidence: 1.0, active: true },
      { from_id: 'pos-enc', to_id: 'embedding', rel_type: 'depends_on', summary: 'Positional encodings are added to the token embeddings before the first layer', confidence: 1.0, active: true },
      // Output
      { from_id: 'softmax', to_id: 'decoder', rel_type: 'depends_on', summary: 'Softmax output layer is applied after the final decoder layer', confidence: 0.95, active: true },
      // Downstream architectures
      { from_id: 'bert', to_id: 'encoder', rel_type: 'depends_on', summary: 'BERT uses only the encoder stack', confidence: 0.95, active: true },
      { from_id: 'gpt', to_id: 'decoder', rel_type: 'depends_on', summary: 'GPT uses only the decoder stack with causal masking', confidence: 1.0, active: true },
      { from_id: 't5', to_id: 'encoder', rel_type: 'depends_on', summary: 'T5 uses both encoder and decoder stacks', confidence: 0.9, active: true },
      { from_id: 't5', to_id: 'decoder', rel_type: 'depends_on', summary: 'T5 uses both encoder and decoder stacks', confidence: 0.9, active: true },
    ],
  },
}

export const HERO_GRAPHS: HeroGraph[] = [LLM_LANDSCAPE, TRANSFORMER_ARCH]
