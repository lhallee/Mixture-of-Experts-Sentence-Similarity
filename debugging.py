import torch


def print_tensor_flow(model, input_tensor):
    names, weights, inputs, outputs = [], [], [], []
    def hook_fn(module, input, output):
        if hasattr(module, 'weight'):
            names.append(module.__class__.__name__)
            weights.append(tuple(module.weight.shape))
            inputs.append(tuple(input[0].shape))
            outputs.append(tuple(output.shape))
        elif 'pool' in module.__class__.__name__.lower():
            names.append(module.__class__.__name__)
            weights.append('None')
            inputs.append(tuple(input[0].shape))
            outputs.append(tuple(output.shape))
    handles = []
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Module):
            handles.append(module.register_forward_hook(hook_fn))
    with torch.no_grad():
        _ = model(input_tensor)
    for handle in handles:
        handle.remove()
    print('Tensor flow')
    print('{:<25} {:<25} {:<25} {:<25}'.format('Layer', 'Weight Size', 'Input size', 'Output size'))
    print('-' * 100)
    for name, weight, input, output in zip(names, weights, inputs, outputs):
        print('{:<25} {:<25} {:<25} {:<25}'.format(str(name), str(weight), str(input), str(output)))


def calc_memory(model, inputs, device, name='Layer'):
    model.to(device)
    try:
        inputs = inputs.to(device)
        memory_before = torch.cuda.memory_allocated(device)
        _ = model(inputs)        
    except:
        inputs = (input.to(device) for input in inputs)
        memory_before = torch.cuda.memory_allocated(device)
        _ = model(*inputs)

    memory_after = torch.cuda.memory_allocated(device)
    vram_usage = memory_after - memory_before
    print(f"Process {name} VRAM usage: {vram_usage / 1024 / 1024:.2f} MB")
    model.cpu()
    del model
    torch.cuda.empty_cache()
